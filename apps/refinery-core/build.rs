fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::compile_protos("../../packages/semantic-spec/proto/aether.proto")?;
    Ok(())
}
